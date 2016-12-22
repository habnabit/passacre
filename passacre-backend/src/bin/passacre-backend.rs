extern crate capnp;
extern crate capnp_rpc;
extern crate gj;
extern crate gjio;
extern crate passacre;

use capnp_rpc::{RpcSystem, twoparty, rpc_twoparty_capnp};
use gj::EventLoop;

use passacre::passacre_capnp::toplevel;

fn main() {
    let args: Vec<String> = ::std::env::args().collect();
    if args.len() != 2 {
        println!("usage: {} <fd>", args[0]);
        return;
    }

    EventLoop::top_level(move |wait_scope| -> Result<(), ::capnp::Error> {
        let mut event_port = try!(::gjio::EventPort::new());
        let stream = {
            let network = event_port.get_network();
            let fd: ::gjio::RawDescriptor = args[1].parse().expect("invalid fd");
            unsafe { network.wrap_raw_socket_descriptor(fd) }.expect("couldn't adopt fd")
        };
        let disconnect_promise = {
            let toplevel =
                toplevel::ToClient::new(passacre::rpc::StandardToplevel).from_server::<::capnp_rpc::Server>();
            let mut network = twoparty::VatNetwork::new(
                stream.clone(), stream, rpc_twoparty_capnp::Side::Server, Default::default());
            let disconnect_promise = network.on_disconnect();
            let rpc_system = RpcSystem::new(Box::new(network), Some(toplevel.client));
            disconnect_promise.attach(rpc_system)
        };

        disconnect_promise.wait(wait_scope, &mut event_port)?;

        Ok(())
    }).expect("top level error");
}
